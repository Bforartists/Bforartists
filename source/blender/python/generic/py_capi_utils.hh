/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup pygen
 */

#pragma once

#include <Python.h>

#include <string>

#include "BLI_compiler_attrs.h"
#include "BLI_span.hh"
#include "BLI_sys_types.h"

/** Useful to print Python objects while debugging. */
void PyC_ObSpit(const char *name, PyObject *var);
/**
 * A version of #PyC_ObSpit that writes into a string (and doesn't take a name argument).
 * Use for logging.
 */
void PyC_ObSpitStr(char *result, size_t result_maxncpy, PyObject *var);
void PyC_LineSpit();
void PyC_StackSpit();

/**
 * Return a string containing the full stack trace.
 *
 * - Only call when `PyErr_Occurred() != 0` .
 * - The exception is left in place without being manipulated,
 *   although they will be normalized in order to display them (`PyErr_Print` also does this).
 * - `SystemExit` exceptions will exit (so `sys.exit(..)` works, matching `PyErr_Print` behavior).
 * - The always returns a Python string (unless exiting where the function doesn't return).
 */
[[nodiscard]] PyObject *PyC_ExceptionBuffer() ATTR_RETURNS_NONNULL;
/**
 * A version of #PyC_ExceptionBuffer that returns the last exception only.
 *
 * Useful for error messages from evaluating numeric expressions for example
 * where a full multi-line stack-trace isn't needed and doesn't format well in the status-bar.
 */
[[nodiscard]] PyObject *PyC_ExceptionBuffer_Simple() ATTR_RETURNS_NONNULL;

[[nodiscard]] PyObject *PyC_Object_GetAttrStringArgs(PyObject *o, Py_ssize_t n, ...);
[[nodiscard]] PyObject *PyC_FrozenSetFromStrings(const char **strings);

/**
 * Similar to #PyErr_Format(),
 *
 * Implementation - we can't actually prepend the existing exception,
 * because it could have _any_ arguments given to it, so instead we get its
 * `__str__` output and raise our own exception including it.
 */
PyObject *PyC_Err_Format_Prefix(PyObject *exception_type_prefix, const char *format, ...);
PyObject *PyC_Err_SetString_Prefix(PyObject *exception_type_prefix, const char *str);

/**
 * Use for Python callbacks run directly from C,
 * when we can't use normal methods of raising exceptions.
 */
void PyC_Err_PrintWithFunc(PyObject *py_func);

void PyC_FileAndNum(const char **r_filename, int *r_lineno);
void PyC_FileAndNum_Safe(const char **r_filename, int *r_lineno); /* checks python is running */
[[nodiscard]] int PyC_AsArray_FAST(void *array,
                                   size_t array_item_size,
                                   PyObject *value_fast,
                                   Py_ssize_t length,
                                   const PyTypeObject *type,
                                   const char *error_prefix);
[[nodiscard]] int PyC_AsArray(void *array,
                              size_t array_item_size,
                              PyObject *value,
                              Py_ssize_t length,
                              const PyTypeObject *type,
                              const char *error_prefix);

[[nodiscard]] int PyC_AsArray_Multi_FAST(void *array,
                                         size_t array_item_size,
                                         PyObject *value_fast,
                                         const int *dims,
                                         int dims_len,
                                         const PyTypeObject *type,
                                         const char *error_prefix);

[[nodiscard]] int PyC_AsArray_Multi(void *array,
                                    size_t array_item_size,
                                    PyObject *value,
                                    const int *dims,
                                    int dims_len,
                                    const PyTypeObject *type,
                                    const char *error_prefix);

[[nodiscard]] PyObject *PyC_Tuple_PackArray_F32(const float *array, uint len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_F64(const double *array, uint len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_I32(const int *array, uint len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_I32FromBool(const int *array, uint len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_Bool(const bool *array, uint len);

/**
 * \note Any errors converting strings will return null with the error left as-is.
 */
[[nodiscard]] PyObject *PyC_Tuple_PackArray_String(const char **array, uint len);

[[nodiscard]] PyObject *PyC_Tuple_PackArray_Multi_F32(const float *array,
                                                      const int dims[],
                                                      int dims_len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_Multi_F64(const double *array,
                                                      const int dims[],
                                                      int dims_len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_Multi_I32(const int *array,
                                                      const int dims[],
                                                      int dims_len);
[[nodiscard]] PyObject *PyC_Tuple_PackArray_Multi_Bool(const bool *array,
                                                       const int dims[],
                                                       int dims_len);

/**
 * Caller needs to ensure tuple is uninitialized.
 * Handy for filling a tuple with None for eg.
 */
void PyC_Tuple_Fill(PyObject *tuple, PyObject *value);
void PyC_List_Fill(PyObject *list, PyObject *value);

/**
 * Create a `str` from bytes in a way which is compatible with non UTF8 encoded file-system paths,
 * see: #111033.
 * Follow http://www.python.org/dev/peps/pep-0383/
 */
[[nodiscard]] PyObject *PyC_UnicodeFromBytes(const char *str);
/**
 * \param size: The length of the string: `strlen(str)`.
 */
[[nodiscard]] PyObject *PyC_UnicodeFromBytesAndSize(const char *str, Py_ssize_t size);
[[nodiscard]] const char *PyC_UnicodeAsBytes(PyObject *py_str,
                                             PyObject **r_coerce); /* coerce must be NULL */
/**
 * String conversion, escape non-unicode chars
 * \param r_size: The string length (not including the null terminator).
 * \note By convention Blender API's use len/length however Python API's use the term size,
 * as this is an alternative to Python's #PyUnicode_AsUTF8AndSize, follow it's naming.
 * \param r_coerce: must reference a pointer set to NULL.
 */
[[nodiscard]] const char *PyC_UnicodeAsBytesAndSize(PyObject *py_str,
                                                    Py_ssize_t *r_size,
                                                    PyObject **r_coerce);

/**
 * Notes on using this structure:
 * - Always initialize to `{nullptr}`.
 * - Always `Py_XDECREF(value_coerce)` before returning,
 *   after this `value` must not be accessed.
 */
struct PyC_UnicodeAsBytesAndSize_Data {
  PyObject *value_coerce;
  const char *value;
  Py_ssize_t value_len;
};

/**
 * Use with PyArg_ParseTuple's "O&" formatting.
 *
 * Expose #PyC_UnicodeAsBytes in a way which is useful to the argument parser.
 * \param o: An argument parsed to #PyC_UnicodeAsBytes.
 * \param p: Pointer to #PyC_UnicodeAsBytes_Data.
 *
 * \note The Python API docs reference `PyUnicode_FSConverter` however this does not support
 * paths which non UTF8 encoding, see: #111033.
 */
int PyC_ParseUnicodeAsBytesAndSize(PyObject *o, void *p);
/** A version of #PyC_ParseUnicodeAsBytesAndSize that accepts None. */
int PyC_ParseUnicodeAsBytesAndSize_OrNone(PyObject *o, void *p);

/**
 * Description: This function creates a new Python dictionary object.
 * NOTE: dict is owned by sys.modules["__main__"] module, reference is borrowed
 * NOTE: important we use the dict from __main__, this is what python expects
 * for 'pickle' to work as well as strings like this...
 * >> foo = 10
 * >> print(__import__("__main__").foo)
 *
 * NOTE: this overwrites __main__ which gives problems with nested calls.
 * be sure to run #PyC_MainModule_Backup & #PyC_MainModule_Restore if there is
 * any chance that python is in the call stack.
 */
[[nodiscard]] PyObject *PyC_DefaultNameSpace(const char *filename) ATTR_NONNULL(1);
void PyC_RunQuicky(const char *filepath, int n, ...) ATTR_NONNULL(1);
/**
 * Import `imports` into `py_dict`.
 *
 * \param py_dict: A Python dictionary, typically used as a name-space for script execution.
 * \param imports: A NULL terminated array of strings.
 * \return true when all modules import without errors, otherwise return false.
 * The caller is expected to handle the exception.
 */
[[nodiscard]] bool PyC_NameSpace_ImportArray(PyObject *py_dict, const char *imports[]);

/**
 * #PyC_MainModule_Restore MUST be called after #PyC_MainModule_Backup.
 */
[[nodiscard]] PyObject *PyC_MainModule_Backup();
void PyC_MainModule_Restore(PyObject *main_mod);

[[nodiscard]] bool PyC_IsInterpreterActive();

/**
 * Generic function to avoid depending on RNA.
 */
[[nodiscard]] void *PyC_RNA_AsPointer(PyObject *value, const char *type_name);

/* flag / set --- interchange */
struct PyC_FlagSet {
  int value;
  const char *identifier;
};

[[nodiscard]] PyObject *PyC_FlagSet_AsString(const PyC_FlagSet *item);
[[nodiscard]] int PyC_FlagSet_ValueFromID_int(const PyC_FlagSet *item,
                                              const char *identifier,
                                              int *r_value);
[[nodiscard]] int PyC_FlagSet_ValueFromID(const PyC_FlagSet *item,
                                          const char *identifier,
                                          int *r_value,
                                          const char *error_prefix);
[[nodiscard]] int PyC_FlagSet_ToBitfield(const PyC_FlagSet *items,
                                         PyObject *value,
                                         int *r_value,
                                         const char *error_prefix);
[[nodiscard]] PyObject *PyC_FlagSet_FromBitfield(PyC_FlagSet *items, int flag);

/**
 * \return success
 *
 * \note it is caller's responsibility to acquire & release GIL!
 */
[[nodiscard]] bool PyC_RunString_AsNumber(const char **imports,
                                          const char *expr,
                                          const char *filename,
                                          double *r_value) ATTR_NONNULL(2, 3, 4);
[[nodiscard]] bool PyC_RunString_AsIntPtr(const char **imports,
                                          const char *expr,
                                          const char *filename,
                                          intptr_t *r_value) ATTR_NONNULL(2, 3, 4);
/**
 * \param r_value_size: The length of the string assigned: `strlen(*r_value)`.
 */
[[nodiscard]] bool PyC_RunString_AsStringAndSize(const char **imports,
                                                 const char *expr,
                                                 const char *filename,
                                                 char **r_value,
                                                 size_t *r_value_size) ATTR_NONNULL(2, 3, 4, 5);
[[nodiscard]] bool PyC_RunString_AsString(const char **imports,
                                          const char *expr,
                                          const char *filename,
                                          char **r_value) ATTR_NONNULL(2, 3, 4);

/**
 * \param r_value_size: The length of the string assigned: `strlen(*r_value)`.
 */
[[nodiscard]] bool PyC_RunString_AsStringAndSizeOrNone(const char **imports,
                                                       const char *expr,
                                                       const char *filename,
                                                       char **r_value,
                                                       size_t *r_value_size) ATTR_NONNULL(2, 3, 4);
[[nodiscard]] bool PyC_RunString_AsStringOrNone(const char **imports,
                                                const char *expr,
                                                const char *filename,
                                                char **r_value) ATTR_NONNULL(2, 3, 4);

/**
 * Flush Python's `sys.stdout` and `sys.stderr`. Errors are ignored.
 */
void PyC_StdFilesFlush();

/**
 * Use with PyArg_ParseTuple's "O&" formatting.
 *
 * \see #PyC_Long_AsBool for a similar function to use outside of argument parsing.
 */
[[nodiscard]] int PyC_ParseBool(PyObject *o, void *p);

struct PyC_StringEnumItems {
  int value;
  const char *id;
};
struct PyC_StringEnum {
  const struct PyC_StringEnumItems *items;
  int value_found;
};

/**
 * Use with PyArg_ParseTuple's "O&" formatting.
 */
[[nodiscard]] int PyC_ParseStringEnum(PyObject *o, void *p);
[[nodiscard]] const char *PyC_StringEnum_FindIDFromValue(const struct PyC_StringEnumItems *items,
                                                         int value);

/**
 * Silly function, we don't use arg. just check its compatible with `__deepcopy__`.
 */
[[nodiscard]] int PyC_CheckArgs_DeepCopy(PyObject *args);

/* Integer parsing (with overflow checks), -1 on error. */
/**
 * Comparison with #PyObject_IsTrue
 * ================================
 *
 * Even though Python provides a way to retrieve the boolean value for an object,
 * in many cases it's far too relaxed, with the following examples coercing values.
 *
 * \code{.py}
 * data.value = "Text"    # True.
 * data.value = ""        # False.
 * data.value = {1, 2}    # True
 * data.value = {}        # False.
 * data.value = None      # False.
 * \endcode
 *
 * In practice this is often a mistake by the script author that doesn't behave as they expect.
 * So it's better to be more strict for attribute assignment and function arguments,
 * only accepting True/False 0/1.
 *
 * If coercing a value is desired, it can be done explicitly: `data.value = bool(value)`
 *
 * \see #PyC_ParseBool for use with #PyArg_ParseTuple and related functions.
 *
 * \note Don't use `bool` return type, so -1 can be used as an error value.
 */
[[nodiscard]] int PyC_Long_AsBool(PyObject *value);
[[nodiscard]] int8_t PyC_Long_AsI8(PyObject *value);
[[nodiscard]] int16_t PyC_Long_AsI16(PyObject *value);
#if 0 /* inline */
[[nodiscard]] int32_t PyC_Long_AsI32(PyObject *value);
[[nodiscard]] int64_t PyC_Long_AsI64(PyObject *value);
#endif

/**
 * Unlike Python's #PyLong_AsUnsignedLong and #PyLong_AsUnsignedLongLong, these unsigned integer
 * parsing functions fall back to calling #PyNumber_Index when their argument is not a
 * `PyLongObject`. This matches Python's signed integer parsing functions which also fall back to
 * calling #PyNumber_Index.
 */
[[nodiscard]] uint8_t PyC_Long_AsU8(PyObject *value);
[[nodiscard]] uint16_t PyC_Long_AsU16(PyObject *value);
[[nodiscard]] uint32_t PyC_Long_AsU32(PyObject *value);
/**
 * #PyLong_AsUnsignedLongLong, unlike #PyLong_AsLongLong, does not fall back to calling
 * #PyNumber_Index when its argument is not a `PyLongObject` instance. To match parsing signed
 * integer types with #PyLong_AsLongLong, this function performs the #PyNumber_Index fallback, if
 * necessary, before calling #PyLong_AsUnsignedLongLong.
 */
[[nodiscard]] uint64_t PyC_Long_AsU64(PyObject *value);

/* inline so type signatures match as expected */
[[nodiscard]] Py_LOCAL_INLINE(int32_t) PyC_Long_AsI32(PyObject *value)
{
#if PY_VERSION_HEX < 0x030d0000 /* <3.13 */
  return (int32_t)_PyLong_AsInt(value);
#else
  return (int32_t)PyLong_AsInt(value);
#endif
}
[[nodiscard]] Py_LOCAL_INLINE(int64_t) PyC_Long_AsI64(PyObject *value)
{
  return (int64_t)PyLong_AsLongLong(value);
}

/* utils for format string in `struct` module style syntax */
[[nodiscard]] char PyC_StructFmt_type_from_str(const char *typestr);
[[nodiscard]] bool PyC_StructFmt_type_is_float_any(char format);
[[nodiscard]] bool PyC_StructFmt_type_is_int_any(char format);
[[nodiscard]] bool PyC_StructFmt_type_is_byte(char format);
[[nodiscard]] bool PyC_StructFmt_type_is_bool(char format);

/**
 * Create a `str` from `std::string`, wraps #PyC_UnicodeFromBytesAndSize.
 */
[[nodiscard]] PyObject *PyC_UnicodeFromStdStr(const std::string &str);

[[nodiscard]] inline PyObject *PyC_Tuple_Pack_F32(const blender::Span<float> values)
{
  return PyC_Tuple_PackArray_F32(values.data(), values.size());
}
[[nodiscard]] inline PyObject *PyC_Tuple_Pack_F64(const blender::Span<double> values)
{
  return PyC_Tuple_PackArray_F64(values.data(), values.size());
}
[[nodiscard]] inline PyObject *PyC_Tuple_Pack_I32(const blender::Span<int> values)
{
  return PyC_Tuple_PackArray_I32(values.data(), values.size());
}
[[nodiscard]] inline PyObject *PyC_Tuple_Pack_I32FromBool(const blender::Span<int> values)
{
  return PyC_Tuple_PackArray_I32FromBool(values.data(), values.size());
}
[[nodiscard]] inline PyObject *PyC_Tuple_Pack_Bool(const blender::Span<bool> values)
{
  return PyC_Tuple_PackArray_Bool(values.data(), values.size());
}

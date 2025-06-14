/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 *
 * \brief Functions and classes for applying templates with variable expressions
 * to filepaths.
 */
#pragma once

#include <cmath>
#include <optional>

#include "BLI_map.hh"
#include "BLI_path_utils.hh"
#include "BLI_string.h"
#include "BLI_string_ref.hh"
#include "BLI_string_utils.hh"

#include "BKE_report.hh"

#include "DNA_scene_types.h"

struct bContext;
struct PointerRNA;
struct PropertyRNA;

namespace blender::bke::path_templates {

/**
 * Variables (names and associated values) for use in template substitution.
 *
 * Note that this is not intended to be persistent storage, but rather is
 * transient for collecting data that is relevant/available in a given
 * templating context.
 *
 * There are currently three supported variable types: string, integer, and
 * float. Names must be unique across all types: you can't have a string *and*
 * integer both with the name "bob".
 */
class VariableMap {
  blender::Map<std::string, std::string> strings_;
  blender::Map<std::string, int64_t> integers_;
  blender::Map<std::string, double> floats_;

 public:
  /**
   * Check if a variable of the given name exists.
   */
  bool contains(blender::StringRef name) const;

  /**
   * Remove the variable with the given name.
   *
   * \return True if the variable existed and was removed, false if it didn't
   * exist in the first place.
   */
  bool remove(blender::StringRef name);

  /**
   * Add a string variable with the given name and value.
   *
   * If there is already a variable with that name, regardless of type, the new
   * variable is *not* added (no overwriting).
   *
   * \return True if the variable was successfully added, false if there was
   * already a variable with that name.
   */
  bool add_string(blender::StringRef name, blender::StringRef value);

  /**
   * Add an integer variable with the given name and value.
   *
   * If there is already a variable with that name, regardless of type, the new
   * variable is *not* added (no overwriting).
   *
   * \return True if the variable was successfully added, false if there was
   * already a variable with that name.
   */
  bool add_integer(blender::StringRef name, int64_t value);

  /**
   * Add a float variable with the given name and value.
   *
   * If there is already a variable with that name, regardless of type, the new
   * variable is *not* added (no overwriting).
   *
   * \return True if the variable was successfully added, false if there was
   * already a variable with that name.
   */
  bool add_float(blender::StringRef name, double value);

  /**
   * Fetch the value of the string variable with the given name.
   *
   * \return The value if a string variable with that name exists,
   * #std::nullopt otherwise.
   */
  std::optional<blender::StringRefNull> get_string(blender::StringRef name) const;

  /**
   * Fetch the value of the integer variable with the given name.
   *
   * \return The value if a integer variable with that name exists,
   * #std::nullopt otherwise.
   */
  std::optional<int64_t> get_integer(blender::StringRef name) const;

  /**
   * Fetch the value of the float variable with the given name.
   *
   * \return The value if a float variable with that name exists,
   * #std::nullopt otherwise.
   */
  std::optional<double> get_float(blender::StringRef name) const;
};

enum class ErrorType {
  UNESCAPED_CURLY_BRACE,
  VARIABLE_SYNTAX,
  FORMAT_SPECIFIER,
  UNKNOWN_VARIABLE,
};

struct Error {
  ErrorType type;
  blender::IndexRange byte_range;
};

bool operator==(const Error &left, const Error &right);

}  // namespace blender::bke::path_templates

/**
 * Build a template variable map for the passed RNA property.
 *
 * \param C: the context to use for building some variables. This is needed in
 * some cases when the property and its owner do not provide the data needed for
 * a variable. This parameter can be null, but the variables it's needed for
 * will then be absent in the returned variable map.
 *
 * \return On success, returns the template variables for the property. If no
 * property is provided or if the property doesn't support path templates,
 * returns #std::nullopt.
 */
std::optional<blender::bke::path_templates::VariableMap> BKE_build_template_variables_for_prop(
    const bContext *C, PointerRNA *ptr, PropertyRNA *prop);

/**
 * Build a template variable map for render output paths.
 *
 * All parameters are allowed to be null, in which case the variables derived
 * from those parameters will simply not be included.
 *
 * This is typically used to create the variables passed to
 * `BKE_path_apply_template()`.
 *
 * \param blend_file_path: full path to the blend file, including the file name.
 * Typically you should fetch this with `ID_BLEND_PATH()`, but there are
 * exceptions. The key thing is that this should be the path to the *relevant*
 * blend file for the context that the variables are going to be used in. For
 * example, if the context is a linked ID then this path should (very likely) be
 * the path to that ID's library blend file, not the currently opened one.
 *
 * \param render_data: used for output resolution and fps. Note for the future:
 * when we add a "current frame number" variable it should *not* come from this
 * parameter, but be passed separately. This is because the callers of this
 * function sometimes have the current frame defined separately from the
 * available RenderData (see e.g. `do_makepicstring()`).
 *
 * \see BKE_path_apply_template()
 *
 * \see BLI_path_abs()
 */
blender::bke::path_templates::VariableMap BKE_build_template_variables_for_render_path(
    const char *blend_file_path, const RenderData *render_data);

/**
 * Check if a path contains any templating syntax at all.
 *
 * This is primarily intended to be used as a pre-check in performance-sensitive
 * code to skip path template processing when it's not needed.
 *
 * \return False if the path contains no templating syntax (no template
 * processing is needed). True if the path does contain templating syntax
 * (template processing *is* needed).
 */
bool BKE_path_contains_template_syntax(blender::StringRef path);

/**
 * Validate the templating in the given path.
 *
 * This produces identical errors as `BKE_path_apply_template()`, but
 * without modifying the path on success.
 *
 * \return An empty vector if the templating in the path is valid, or a vector
 * of the errors if invalid.
 *
 * \see BKE_path_apply_template()
 */
blender::Vector<blender::bke::path_templates::Error> BKE_path_validate_template(
    blender::StringRef path, const blender::bke::path_templates::VariableMap &template_variables);

/**
 * Perform variable substitution and escaping on the given path.
 *
 * This mutates the path in-place. `path` must be a null-terminated string.
 *
 * The syntax for template expressions is `{variable_name}` or
 * {variable_name:format_spec}`. The format specification syntax currently only
 * applies to numerical values (integer or float), and uses hash symbols (#) to
 * indicate the number of digits to print the number with. It can be in any of
 * the following forms:
 *
 * - `####`: format as an integer with at least 4 digits, padding with zeros as
 *   needed.
 * - `.###`: format as a float with precisely 3 fractional digits.
 * - `##.###`: format as a float with at least 2 integer-part digits (padded
 *   with zeros as necessary) and precisely 3 fractional-part digits.
 *
 * This function also processes a simple escape sequence for writing literal "{"
 * and "}": like Python format strings, double braces "{{" and "}}" are treated
 * as escape sequences for "{" and "}", and are substituted appropriately. Note
 * that this substitution only happens *outside* of the variable syntax, and
 * therefore cannot e.g. be used inside variable names.
 *
 * If any errors are encountered, the path is left unaltered and a list of all
 * errors encountered is returned. Errors include:
 *
 * - Variable expression syntax errors.
 * - Unescaped curly braces.
 * - Referenced variables that cannot be found.
 * - Format specifications that don't apply to the type of variable they're
 *   paired with.
 *
 * \param path_max_length The maximum length that template expansion is allowed
 * to make the template-expanded path (in bytes), including the null terminator.
 * In general, this should be the size of the underlying allocation of `path`.
 *
 * \return On success, an empty vector. If there are errors, a vector of all
 * errors encountered.
 */
blender::Vector<blender::bke::path_templates::Error> BKE_path_apply_template(
    char *path,
    int path_max_length,
    const blender::bke::path_templates::VariableMap &template_variables);
/**
 * Produces a human-readable error message for the given template error.
 */
std::string BKE_path_template_error_to_string(const blender::bke::path_templates::Error &error,
                                              blender::StringRef path);

/**
 * Logs a report for the given template errors, with human-readable error
 * messages.
 */
void BKE_report_path_template_errors(ReportList *reports,
                                     eReportType report_type,
                                     blender::StringRef path,
                                     blender::Span<blender::bke::path_templates::Error> errors);

/**
 * Format the given floating point value with the provided format specifier. The format specifier
 * is e.g. the "##.###" in "{name:##.###}".
 *
 * \return #std::nullopt if the format specifier is invalid.
 */
std::optional<std::string> BKE_path_template_format_float(blender::StringRef format_specifier,
                                                          double value);

/** Same as #BKE_path_template_format_float but for formatting an integer value.  */
std::optional<std::string> BKE_path_template_format_int(blender::StringRef format_specifier,
                                                        int64_t value);

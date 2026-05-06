/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup blt
 *
 * This allows converting std::tm datetime structures to localized date and
 * time strings. The localization is based on the CLDR from the current locale.
 */

#include <ctime>
#include <string>

#include "BLI_string_ref.hh"

namespace blender::date_string {

enum class DateFormat : uint8_t {
  Default = 0,  /* Convention based on output language. */
  LE_Slash = 1, /* dd/mm/yyyy */
  LE_Dot = 2,   /* dd.mm.yyyy */
  LE_Dash = 3,  /* dd-mm-yyyy */
  ME_Slash = 4, /* mm/dd/yyyy */
  BE_Slash = 5, /* yyyy/mm/dd */
  BE_Dot = 6,   /* yyyy.mm.dd */
  BE_Dash = 7,  /* yyyy-mm-dd */
};

enum class TimeFormat : uint8_t {
  H24 = 0, /* 23:59 */
  H12 = 1, /* 11:59 PM */
};

std::string date(const std::tm &date_time,
                 StringRef locale_iso = {},
                 DateFormat format = DateFormat::Default);

std::string time(const std::tm &date_time, TimeFormat format = TimeFormat::H24);

std::string datetime(const std::tm &date_time,
                     StringRef locale_iso = {},
                     DateFormat date_format = DateFormat::Default,
                     TimeFormat time_format = TimeFormat::H24,
                     const std::tm *now = nullptr,
                     StringRef today = {},
                     StringRef yesterday = {});

}  // namespace blender::date_string

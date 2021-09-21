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

#pragma once

/** \file
 * \ingroup bli
 *
 * Functions for generating and handling UUID structs according to RFC4122.
 *
 * Note that these are true UUIDs, not to be confused with the "session uuid" defined in
 * `BLI_session_uuid.h`.
 */
#include "DNA_uuid_types.h"

#include "BLI_compiler_attrs.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * UUID generator for random (version 4) UUIDs. See RFC4122 section 4.4.
 * This function is not thread-safe. */
bUUID BLI_uuid_generate_random(void);

/**
 * Return the UUID nil value, consisting of all-zero fields.
 */
bUUID BLI_uuid_nil(void);

/** Return true only if this is the nil UUID. */
bool BLI_uuid_is_nil(bUUID uuid);

/** Compare two UUIDs, return true only if they are equal. */
bool BLI_uuid_equal(bUUID uuid1, bUUID uuid2);

/**
 * Format UUID as string.
 * The buffer must be at least 37 bytes (36 bytes for the UUID + terminating 0).
 * Use `UUID_STRING_LEN` from DNA_uuid_types.h if you want to use a constant for this.
 */
void BLI_uuid_format(char *buffer, bUUID uuid) ATTR_NONNULL();

/**
 * Parse a string as UUID.
 * The string MUST be in the format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`,
 * as produced by #BLI_uuid_format().
 *
 * Return true if the string could be parsed, and false otherwise. In the latter case, the UUID may
 * have been partially updated.
 */
bool BLI_uuid_parse_string(bUUID *uuid, const char *buffer) ATTR_NONNULL();

#ifdef __cplusplus
}

#  include <ostream>

/** Output the UUID as formatted ASCII string, see #BLI_uuid_format(). */
std::ostream &operator<<(std::ostream &stream, bUUID uuid);

#endif

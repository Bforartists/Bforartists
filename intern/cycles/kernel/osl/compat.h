/* SPDX-FileCopyrightText: 2011-2023 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#pragma once

#include <OSL/oslconfig.h>

CCL_NAMESPACE_BEGIN

#if OSL_LIBRARY_VERSION_CODE >= 11302
using OSLUStringHash = OSL::ustringhash;
#  if OSL_LIBRARY_VERSION_CODE >= 11400
using OSLUStringRep = OSL::ustringhash;
#  else
using OSLUStringRep = OSL::ustringrep;
#  endif

static inline OSL::ustring to_ustring(OSLUStringHash h)
{
  return OSL::ustring::from_hash(h.hash());
}

#else
using OSLUStringHash = OSL::ustring;
using OSLUStringRep = OSL::ustring;

static inline OSL::ustring to_ustring(OSLUStringHash h)
{
  return h;
}
#endif

CCL_NAMESPACE_END

/* SPDX-FileCopyrightText: 2013 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "opensubdiv_capi_type.hh"

// Global initialization/deinitialization.
//
// Supposed to be called from main thread.
void openSubdiv_init();
void openSubdiv_cleanup();

int openSubdiv_getVersionHex();

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

/** \file
 * \ingroup GHOST
 * Declaration of GHOST_DisplayManagerNULL class.
 */

#pragma once

#include "GHOST_DisplayManager.h"
#include "GHOST_SystemNULL.h"

class GHOST_SystemNULL;

class GHOST_DisplayManagerNULL : public GHOST_DisplayManager {
 public:
  GHOST_DisplayManagerNULL(GHOST_SystemNULL *system) : GHOST_DisplayManager(), m_system(system)
  { /* nop */
  }
  GHOST_TSuccess getNumDisplays(uint8_t &numDisplays) const
  {
    return GHOST_kFailure;
  }
  GHOST_TSuccess getNumDisplaySettings(uint8_t display, int32_t &numSettings) const
  {
    return GHOST_kFailure;
  }
  GHOST_TSuccess getDisplaySetting(uint8_t display,
                                   int32_t index,
                                   GHOST_DisplaySetting &setting) const
  {
    return GHOST_kFailure;
  }
  GHOST_TSuccess getCurrentDisplaySetting(uint8_t display, GHOST_DisplaySetting &setting) const
  {
    return getDisplaySetting(display, int32_t(0), setting);
  }
  GHOST_TSuccess setCurrentDisplaySetting(uint8_t display, const GHOST_DisplaySetting &setting)
  {
    return GHOST_kSuccess;
  }

 private:
  GHOST_SystemNULL *m_system;
};

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
 */

#define _USE_MATH_DEFINES

#include "GHOST_Wintab.h"

GHOST_Wintab *GHOST_Wintab::loadWintab(HWND hwnd)
{
  /* Load Wintab library if available. */

  auto handle = unique_hmodule(::LoadLibrary("Wintab32.dll"), &::FreeLibrary);
  if (!handle) {
    return nullptr;
  }

  /* Get Wintab functions. */

  auto info = (GHOST_WIN32_WTInfo)::GetProcAddress(handle.get(), "WTInfoA");
  if (!info) {
    return nullptr;
  }

  auto open = (GHOST_WIN32_WTOpen)::GetProcAddress(handle.get(), "WTOpenA");
  if (!open) {
    return nullptr;
  }

  auto get = (GHOST_WIN32_WTGet)::GetProcAddress(handle.get(), "WTGetA");
  if (!get) {
    return nullptr;
  }

  auto set = (GHOST_WIN32_WTSet)::GetProcAddress(handle.get(), "WTSetA");
  if (!set) {
    return nullptr;
  }

  auto close = (GHOST_WIN32_WTClose)::GetProcAddress(handle.get(), "WTClose");
  if (!close) {
    return nullptr;
  }

  auto packetsGet = (GHOST_WIN32_WTPacketsGet)::GetProcAddress(handle.get(), "WTPacketsGet");
  if (!packetsGet) {
    return nullptr;
  }

  auto queueSizeGet = (GHOST_WIN32_WTQueueSizeGet)::GetProcAddress(handle.get(), "WTQueueSizeGet");
  if (!queueSizeGet) {
    return nullptr;
  }

  auto queueSizeSet = (GHOST_WIN32_WTQueueSizeSet)::GetProcAddress(handle.get(), "WTQueueSizeSet");
  if (!queueSizeSet) {
    return nullptr;
  }

  auto enable = (GHOST_WIN32_WTEnable)::GetProcAddress(handle.get(), "WTEnable");
  if (!enable) {
    return nullptr;
  }

  auto overlap = (GHOST_WIN32_WTOverlap)::GetProcAddress(handle.get(), "WTOverlap");
  if (!overlap) {
    return nullptr;
  }

  /* Build Wintab context. */

  LOGCONTEXT lc = {0};
  if (!info(WTI_DEFSYSCTX, 0, &lc)) {
    return nullptr;
  }

  Coord tablet, system;
  extractCoordinates(lc, tablet, system);
  modifyContext(lc);

  /* The Wintab spec says we must open the context disabled if we are using cursor masks. */
  auto hctx = unique_hctx(open(hwnd, &lc, FALSE), close);
  if (!hctx) {
    return nullptr;
  }

  /* Wintab provides no way to determine the maximum queue size aside from checking if attempts
   * to change the queue size are successful. */
  const int maxQueue = 500;
  int queueSize = queueSizeGet(hctx.get());

  while (queueSize < maxQueue) {
    int testSize = min(queueSize + 16, maxQueue);
    if (queueSizeSet(hctx.get(), testSize)) {
      queueSize = testSize;
    }
    else {
      /* From Windows Wintab Documentation for WTQueueSizeSet:
       * "If the return value is zero, the context has no queue because the function deletes the
       * original queue before attempting to create a new one. The application must continue
       * calling the function with a smaller queue size until the function returns a non - zero
       * value."
       *
       * In our case we start with a known valid queue size and in the event of failure roll
       * back to the last valid queue size. The Wintab spec dates back to 16 bit Windows, thus
       * assumes memory recently deallocated may not be available, which is no longer a practical
       * concern. */
      if (!queueSizeSet(hctx.get(), queueSize)) {
        /* If a previously valid queue size is no longer valid, there is likely something wrong in
         * the Wintab implementation and we should not use it. */
        return nullptr;
      }
      break;
    }
  }

  return new GHOST_Wintab(hwnd,
                          std::move(handle),
                          info,
                          get,
                          set,
                          packetsGet,
                          enable,
                          overlap,
                          std::move(hctx),
                          tablet,
                          system,
                          queueSize);
}

void GHOST_Wintab::modifyContext(LOGCONTEXT &lc)
{
  lc.lcPktData = PACKETDATA;
  lc.lcPktMode = PACKETMODE;
  lc.lcMoveMask = PACKETDATA;
  lc.lcOptions |= CXO_CSRMESSAGES | CXO_MESSAGES;

  /* Tablet scaling is handled manually because some drivers don't handle HIDPI or multi-display
   * correctly; reset tablet scale factors to un-scaled tablet coordinates. */
  lc.lcOutOrgX = lc.lcInOrgX;
  lc.lcOutOrgY = lc.lcInOrgY;
  lc.lcOutExtX = lc.lcInExtX;
  lc.lcOutExtY = lc.lcInExtY;
}

void GHOST_Wintab::extractCoordinates(LOGCONTEXT &lc, Coord &tablet, Coord &system)
{
  tablet.x.org = lc.lcInOrgX;
  tablet.x.ext = lc.lcInExtX;
  tablet.y.org = lc.lcInOrgY;
  tablet.y.ext = lc.lcInExtY;

  system.x.org = lc.lcSysOrgX;
  system.x.ext = lc.lcSysExtX;
  system.y.org = lc.lcSysOrgY;
  /* Wintab maps y origin to the tablet's bottom; invert y to match Windows y origin mapping to the
   * screen top. */
  system.y.ext = -lc.lcSysExtY;
}

GHOST_Wintab::GHOST_Wintab(HWND hwnd,
                           unique_hmodule handle,
                           GHOST_WIN32_WTInfo info,
                           GHOST_WIN32_WTGet get,
                           GHOST_WIN32_WTSet set,
                           GHOST_WIN32_WTPacketsGet packetsGet,
                           GHOST_WIN32_WTEnable enable,
                           GHOST_WIN32_WTOverlap overlap,
                           unique_hctx hctx,
                           Coord tablet,
                           Coord system,
                           int queueSize)
    : m_handle{std::move(handle)},
      m_fpInfo{info},
      m_fpGet{get},
      m_fpSet{set},
      m_fpPacketsGet{packetsGet},
      m_fpEnable{enable},
      m_fpOverlap{overlap},
      m_context{std::move(hctx)},
      m_tabletCoord{tablet},
      m_systemCoord{system},
      m_pkts{queueSize}
{
  m_fpInfo(WTI_INTERFACE, IFC_NDEVICES, &m_numDevices);
  updateCursorInfo();
}

void GHOST_Wintab::enable()
{
  m_fpEnable(m_context.get(), true);
  m_enabled = true;
}

void GHOST_Wintab::disable()
{
  if (m_focused) {
    loseFocus();
  }
  m_fpEnable(m_context.get(), false);
  m_enabled = false;
}

void GHOST_Wintab::gainFocus()
{
  m_fpOverlap(m_context.get(), true);
  m_focused = true;
}

void GHOST_Wintab::loseFocus()
{
  if (m_lastTabletData.Active != GHOST_kTabletModeNone) {
    leaveRange();
  }

  /* Mouse mode of tablet or display layout may change when Wintab or Window is inactive. Don't
   * trust for mouse movement until re-verified. */
  m_coordTrusted = false;

  m_fpOverlap(m_context.get(), false);
  m_focused = false;
}

void GHOST_Wintab::leaveRange()
{
  /* Button state can't be tracked while out of range, reset it. */
  m_buttons = 0;
  /* Set to none to indicate tablet is inactive. */
  m_lastTabletData = GHOST_TABLET_DATA_NONE;
  /* Clear the packet queue. */
  m_fpPacketsGet(m_context.get(), m_pkts.size(), m_pkts.data());
}

void GHOST_Wintab::remapCoordinates()
{
  LOGCONTEXT lc = {0};

  if (m_fpInfo(WTI_DEFSYSCTX, 0, &lc)) {
    extractCoordinates(lc, m_tabletCoord, m_systemCoord);
    modifyContext(lc);

    m_fpSet(m_context.get(), &lc);
  }
}

void GHOST_Wintab::updateCursorInfo()
{
  AXIS Pressure, Orientation[3];

  BOOL pressureSupport = m_fpInfo(WTI_DEVICES, DVC_NPRESSURE, &Pressure);
  m_maxPressure = pressureSupport ? Pressure.axMax : 0;

  BOOL tiltSupport = m_fpInfo(WTI_DEVICES, DVC_ORIENTATION, &Orientation);
  /* Check if tablet supports azimuth [0] and altitude [1], encoded in axResolution. */
  if (tiltSupport && Orientation[0].axResolution && Orientation[1].axResolution) {
    m_maxAzimuth = Orientation[0].axMax;
    m_maxAltitude = Orientation[1].axMax;
  }
  else {
    m_maxAzimuth = m_maxAltitude = 0;
  }
}

void GHOST_Wintab::processInfoChange(LPARAM lParam)
{
  /* Update number of connected Wintab digitizers. */
  if (LOWORD(lParam) == WTI_INTERFACE && HIWORD(lParam) == IFC_NDEVICES) {
    m_fpInfo(WTI_INTERFACE, IFC_NDEVICES, &m_numDevices);
  }
}

bool GHOST_Wintab::devicesPresent()
{
  return m_numDevices > 0;
}

GHOST_TabletData GHOST_Wintab::getLastTabletData()
{
  return m_lastTabletData;
}

void GHOST_Wintab::getInput(std::vector<GHOST_WintabInfoWin32> &outWintabInfo)
{
  const int numPackets = m_fpPacketsGet(m_context.get(), m_pkts.size(), m_pkts.data());
  outWintabInfo.resize(numPackets);
  size_t outExtent = 0;

  for (int i = 0; i < numPackets; i++) {
    PACKET pkt = m_pkts[i];
    GHOST_WintabInfoWin32 &out = outWintabInfo[i + outExtent];

    out.tabletData = GHOST_TABLET_DATA_NONE;
    /* % 3 for multiple devices ("DualTrack"). */
    switch (pkt.pkCursor % 3) {
      case 0:
        /* Puck - processed as mouse. */
        out.tabletData.Active = GHOST_kTabletModeNone;
        break;
      case 1:
        out.tabletData.Active = GHOST_kTabletModeStylus;
        break;
      case 2:
        out.tabletData.Active = GHOST_kTabletModeEraser;
        break;
    }

    out.x = pkt.pkX;
    out.y = pkt.pkY;

    if (m_maxPressure > 0) {
      out.tabletData.Pressure = (float)pkt.pkNormalPressure / (float)m_maxPressure;
    }

    if ((m_maxAzimuth > 0) && (m_maxAltitude > 0)) {
      ORIENTATION ort = pkt.pkOrientation;
      float vecLen;
      float altRad, azmRad; /* In radians. */

      /*
       * From the wintab spec:
       * orAzimuth: Specifies the clockwise rotation of the cursor about the z axis through a
       * full circular range.
       * orAltitude: Specifies the angle with the x-y plane through a signed, semicircular range.
       * Positive values specify an angle upward toward the positive z axis; negative values
       * specify an angle downward toward the negative z axis.
       *
       * wintab.h defines orAltitude as a UINT but documents orAltitude as positive for upward
       * angles and negative for downward angles. WACOM uses negative altitude values to show that
       * the pen is inverted; therefore we cast orAltitude as an (int) and then use the absolute
       * value.
       */

      /* Convert raw fixed point data to radians. */
      altRad = (float)((fabs((float)ort.orAltitude) / (float)m_maxAltitude) * M_PI / 2.0);
      azmRad = (float)(((float)ort.orAzimuth / (float)m_maxAzimuth) * M_PI * 2.0);

      /* Find length of the stylus' projected vector on the XY plane. */
      vecLen = cos(altRad);

      /* From there calculate X and Y components based on azimuth. */
      out.tabletData.Xtilt = sin(azmRad) * vecLen;
      out.tabletData.Ytilt = (float)(sin(M_PI / 2.0 - azmRad) * vecLen);
    }

    out.time = pkt.pkTime;

    /* Some Wintab libraries don't handle relative button input, so we track button presses
     * manually. */
    out.button = GHOST_kButtonMaskNone;
    out.type = GHOST_kEventCursorMove;

    DWORD buttonsChanged = m_buttons ^ pkt.pkButtons;
    WORD buttonIndex = 0;
    GHOST_WintabInfoWin32 buttonRef = out;
    int buttons = 0;

    while (buttonsChanged) {
      if (buttonsChanged & 1) {
        /* Find the index for the changed button from the button map. */
        GHOST_TButtonMask button = mapWintabToGhostButton(pkt.pkCursor, buttonIndex);

        if (button != GHOST_kButtonMaskNone) {
          /* Extend output if multiple buttons are pressed. We don't extend input until we confirm
           * a Wintab buttons maps to a system button. */
          if (buttons > 0) {
            outWintabInfo.resize(outWintabInfo.size() + 1);
            outExtent++;
            GHOST_WintabInfoWin32 &out = outWintabInfo[i + outExtent];
            out = buttonRef;
          }
          buttons++;

          out.button = button;
          if (buttonsChanged & pkt.pkButtons) {
            out.type = GHOST_kEventButtonDown;
          }
          else {
            out.type = GHOST_kEventButtonUp;
          }
        }

        m_buttons ^= 1 << buttonIndex;
      }

      buttonsChanged >>= 1;
      buttonIndex++;
    }
  }

  if (!outWintabInfo.empty()) {
    m_lastTabletData = outWintabInfo.back().tabletData;
  }
}

GHOST_TButtonMask GHOST_Wintab::mapWintabToGhostButton(UINT cursor, WORD physicalButton)
{
  const WORD numButtons = 32;
  BYTE logicalButtons[numButtons] = {0};
  BYTE systemButtons[numButtons] = {0};

  if (!m_fpInfo(WTI_CURSORS + cursor, CSR_BUTTONMAP, &logicalButtons) ||
      !m_fpInfo(WTI_CURSORS + cursor, CSR_SYSBTNMAP, &systemButtons)) {
    return GHOST_kButtonMaskNone;
  }

  if (physicalButton >= numButtons) {
    return GHOST_kButtonMaskNone;
  }

  BYTE lb = logicalButtons[physicalButton];

  if (lb >= numButtons) {
    return GHOST_kButtonMaskNone;
  }

  switch (systemButtons[lb]) {
    case SBN_LCLICK:
      return GHOST_kButtonMaskLeft;
    case SBN_RCLICK:
      return GHOST_kButtonMaskRight;
    case SBN_MCLICK:
      return GHOST_kButtonMaskMiddle;
    default:
      return GHOST_kButtonMaskNone;
  }
}

void GHOST_Wintab::mapWintabToSysCoordinates(int x_in, int y_in, int &x_out, int &y_out)
{
  /* Maps from range [in.org, in.org + abs(in.ext)] to [out.org, out.org + abs(out.ext)], in
   * reverse if in.ext and out.ext have differing sign. */
  auto remap = [](int inPoint, Range in, Range out) -> int {
    int absInExt = abs(in.ext);
    int absOutExt = abs(out.ext);

    /* Translate input from range [in.org, in.org + absInExt] to [0, absInExt] */
    int inMagnitude = inPoint - in.org;

    /* If signs of extents differ, reverse input over range. */
    if ((in.ext < 0) != (out.ext < 0)) {
      inMagnitude = absInExt - inMagnitude;
    }

    /* Scale from [0, absInExt] to [0, absOutExt]. */
    int outMagnitude = inMagnitude * absOutExt / absInExt;

    /* Translate from range [0, absOutExt] to [out.org, out.org + absOutExt]. */
    int outPoint = outMagnitude + out.org;

    return outPoint;
  };

  x_out = remap(x_in, m_tabletCoord.x, m_systemCoord.x);
  y_out = remap(y_in, m_tabletCoord.y, m_systemCoord.y);
}

bool GHOST_Wintab::trustCoordinates()
{
  return m_coordTrusted;
}

bool GHOST_Wintab::testCoordinates(int sysX, int sysY, int wtX, int wtY)
{
  mapWintabToSysCoordinates(wtX, wtY, wtX, wtY);

  /* Allow off by one pixel tolerance in case of rounding error. */
  if (abs(sysX - wtX) <= 1 && abs(sysY - wtY) <= 1) {
    m_coordTrusted = true;
    return true;
  }
  else {
    m_coordTrusted = false;
    return false;
  }
}

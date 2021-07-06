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
 * Declaration of GHOST_SystemWayland class.
 */

#pragma once

#include "../GHOST_Types.h"
#include "GHOST_System.h"
#include "GHOST_WindowWayland.h"

#include <wayland-client.h>
#include <xdg-decoration-client-protocol.h>
#include <xdg-shell-client-protocol.h>

#include <string>

class GHOST_WindowWayland;

struct display_t;

struct output_t {
  struct wl_output *output;
  int32_t width_pxl, height_pxl;  // dimensions in pixel
  int32_t width_mm, height_mm;    // dimensions in millimeter
  int transform;
  int scale;
  std::string make;
  std::string model;
};

class GHOST_SystemWayland : public GHOST_System {
 public:
  GHOST_SystemWayland();

  ~GHOST_SystemWayland() override;

  bool processEvents(bool waitForEvent) override;

  int toggleConsole(int action) override;

  GHOST_TSuccess getModifierKeys(GHOST_ModifierKeys &keys) const override;

  GHOST_TSuccess getButtons(GHOST_Buttons &buttons) const override;

  char *getClipboard(bool selection) const override;

  void putClipboard(const char *buffer, bool selection) const override;

  uint8_t getNumDisplays() const override;

  GHOST_TSuccess getCursorPosition(int32_t &x, int32_t &y) const override;

  GHOST_TSuccess setCursorPosition(int32_t x, int32_t y) override;

  void getMainDisplayDimensions(uint32_t &width, uint32_t &height) const override;

  void getAllDisplayDimensions(uint32_t &width, uint32_t &height) const override;

  GHOST_IContext *createOffscreenContext(GHOST_GLSettings glSettings) override;

  GHOST_TSuccess disposeContext(GHOST_IContext *context) override;

  GHOST_IWindow *createWindow(const char *title,
                              int32_t left,
                              int32_t top,
                              uint32_t width,
                              uint32_t height,
                              GHOST_TWindowState state,
                              GHOST_TDrawingContextType type,
                              GHOST_GLSettings glSettings,
                              const bool exclusive,
                              const bool is_dialog,
                              const GHOST_IWindow *parentWindow) override;

  wl_display *display();

  wl_compositor *compositor();

  xdg_wm_base *shell();

  zxdg_decoration_manager_v1 *decoration_manager();

  const std::vector<output_t *> &outputs() const;

  wl_shm *shm() const;

  void setSelection(const std::string &selection);

  GHOST_TSuccess setCursorShape(GHOST_TStandardCursor shape);

  GHOST_TSuccess hasCursorShape(GHOST_TStandardCursor cursorShape);

  GHOST_TSuccess setCustomCursorShape(uint8_t *bitmap,
                                      uint8_t *mask,
                                      int sizex,
                                      int sizey,
                                      int hotX,
                                      int hotY,
                                      bool canInvertColor);

  GHOST_TSuccess setCursorVisibility(bool visible);

  GHOST_TSuccess setCursorGrab(const GHOST_TGrabCursorMode mode, wl_surface *surface);

 private:
  struct display_t *d;
  std::string selection;
};

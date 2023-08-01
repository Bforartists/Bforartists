/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 */

#pragma once

#include "GHOST_SystemWin32.hh"
#include "GHOST_WindowWin32.hh"
#include <GHOST_Types.h>
#include <string.h>

class GHOST_DropTargetWin32 : public IDropTarget {
 public:
  /* IUnknownd implementation.
   * Enables clients to get pointers to other interfaces on a given object
   * through the QueryInterface method, and manage the existence of the object
   * through the AddRef and Release methods. All other COM interfaces are
   * inherited, directly or indirectly, from IUnknown. Therefore, the three
   * methods in IUnknown are the first entries in the VTable for every interface.
   */
  HRESULT __stdcall QueryInterface(REFIID riid, void **ppv_obj);
  ULONG __stdcall AddRef(void);
  ULONG __stdcall Release(void);

  /* IDropTarget implementation
   * + The IDropTarget interface is one of the interfaces you implement to
   *   provide drag-and-drop operations in your application. It contains methods
   *   used in any application that can be a target for data during a
   *   drag-and-drop operation. A drop-target application is responsible for:
   *
   *  - Determining the effect of the drop on the target application.
   *  - Incorporating any valid dropped data when the drop occurs.
   *  - Communicating target feedback to the source so the source application
   *    can provide appropriate visual feedback such as setting the cursor.
   *  - Implementing drag scrolling.
   *  - Registering and revoking its application windows as drop targets.
   *
   * The IDropTarget interface contains methods that handle all these
   * responsibilities except registering and revoking the application window
   * as a drop target, for which you must call the RegisterDragDrop and the
   * RevokeDragDrop functions.
   */

  HRESULT __stdcall DragEnter(IDataObject *p_data_object,
                              DWORD grf_key_state,
                              POINTL pt,
                              DWORD *pdw_effect);
  HRESULT __stdcall DragOver(DWORD grf_key_state, POINTL pt, DWORD *pdw_effect);
  HRESULT __stdcall DragLeave(void);
  HRESULT __stdcall Drop(IDataObject *p_data_object,
                         DWORD grf_key_state,
                         POINTL pt,
                         DWORD *pdw_effect);

  /**
   * Constructor
   * With the modifier keys, we want to distinguish left and right keys.
   * Sometimes this is not possible (Windows ME for instance). Then, we want
   * events generated for both keys.
   * \param window: The window to register as drop target.
   * \param system: The associated system.
   */
  GHOST_DropTargetWin32(GHOST_WindowWin32 *window, GHOST_SystemWin32 *system);

  /**
   * Destructor
   * Do NOT destroy directly. Use Release() instead to make COM happy.
   */
  ~GHOST_DropTargetWin32();

 private:
  /* Internal helper functions */

  /**
   * Base the effect on those allowed by the drop-source.
   * \param dwAllowed: Drop sources allowed drop effect.
   * \return The allowed drop effect.
   */
  DWORD allowedDropEffect(DWORD dw_allowed);

  /**
   * Query DataObject for the data types it supports.
   * \param p_data_object: Pointer to the DataObject.
   * \return GHOST data type.
   */
  GHOST_TDragnDropTypes getGhostType(IDataObject *p_data_object);

  /**
   * Get data to pass in event.
   * It checks the type and calls specific functions for each type.
   * \param p_data_object: Pointer to the DataObject.
   * \return Pointer to data.
   */
  void *getGhostData(IDataObject *p_data_object);

  /**
   * Allocate data as file array to pass in event.
   * \param p_data_object: Pointer to the DataObject.
   * \return Pointer to data.
   */
  void *getDropDataAsFilenames(IDataObject *p_data_object);

  /**
   * Allocate data as string to pass in event.
   * \param p_data_object: Pointer to the DataObject.
   * \return Pointer to data.
   */
  void *getDropDataAsString(IDataObject *p_data_object);

  /**
   * Convert Unicode to ANSI, replacing uncomfortable chars with '?'.
   * The ANSI codepage is the system default codepage,
   * and can change from system to system.
   * \param in: LPCWSTR.
   * \param out: char *. Is set to nullptr on failure.
   * \return 0 on failure. Else the size of the string including '\0'.
   */
  int WideCharToANSI(LPCWSTR in, char *&out);

  /* Private member variables */
  /* COM reference count. */
  LONG m_cRef;
  /* Handle of the associated window. */
  HWND m_hWnd;
  /* The associated GHOST_WindowWin32. */
  GHOST_WindowWin32 *m_window;
  /* The System. */
  GHOST_SystemWin32 *m_system;
  /* Data type of the dragged object */
  GHOST_TDragnDropTypes m_draggedObjectType;

#ifdef WITH_CXX_GUARDEDALLOC
  MEM_CXX_CLASS_ALLOC_FUNCS("GHOST:GHOST_DropTargetWin32")
#endif
};
